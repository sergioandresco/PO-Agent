import * as path from "node:path";
import * as cdk from "aws-cdk-lib";
import { HttpApi, HttpMethod } from "aws-cdk-lib/aws-apigatewayv2";
import { HttpLambdaIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { SqsEventSource } from "aws-cdk-lib/aws-lambda-event-sources";
import * as logs from "aws-cdk-lib/aws-logs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sqs from "aws-cdk-lib/aws-sqs";
import type { Construct } from "constructs";

export interface PoAgentStackProps extends cdk.StackProps {
  /** Origin allowed to call the API. The deployed frontend, not "*". */
  readonly corsAllowedOrigins: string;
  readonly llmProvider: string;
  readonly llmModel: string;
}

/** Where the SecureString parameters live. Created out of band — see below. */
const PARAMETER_PREFIX = "/po-agent";
const CLERK_SECRET_PARAM = `${PARAMETER_PREFIX}/clerk-secret-key`;
const LLM_API_KEY_PARAM = `${PARAMETER_PREFIX}/llm-api-key`;

/**
 * Phase 1 of the backend: everything except the per-stage split.
 *
 * POST /jobs writes the transcript to S3, records the job in DynamoDB and drops
 * a message on SQS; a worker Lambda picks it up and runs the whole pipeline. The
 * pipeline still executes as one function rather than as seven — that is phase 2
 * (Step Functions), and none of the resources here change when it lands.
 *
 * The worker's 15-minute ceiling is the known limitation of this shape. It is
 * enough for the transcript sizes the project works with today, and it is the
 * reason phase 2 exists.
 */
export class PoAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: PoAgentStackProps) {
    super(scope, id, props);

    // ---- storage --------------------------------------------------------

    // Single table, keys per CLAUDE.md §6. RemovalPolicy.DESTROY is deliberate:
    // this is an academic project that will be torn down, and leaving orphaned
    // tables behind after `cdk destroy` is worse than losing test jobs. Switch to
    // RETAIN the moment real data lands here.
    const table = new dynamodb.Table(this, "Table", {
      partitionKey: { name: "pk", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "sk", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: false },
    });

    table.addGlobalSecondaryIndex({
      indexName: "gsi1",
      partitionKey: { name: "gsi1pk", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "gsi1sk", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    const transcripts = new s3.Bucket(this, "Transcripts", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      lifecycleRules: [
        // Transcripts are an input, not an archive. Ninety days is well past the
        // life of any experiment run and keeps storage at effectively zero.
        { id: "expire-transcripts", expiration: cdk.Duration.days(90) },
      ],
    });

    // ---- queue ----------------------------------------------------------

    const deadLetterQueue = new sqs.Queue(this, "JobsDlq", {
      retentionPeriod: cdk.Duration.days(14),
      enforceSSL: true,
    });

    // Visibility timeout must exceed the worker's timeout, or SQS hands the same
    // job to a second worker while the first is still paying for LLM calls.
    const jobs = new sqs.Queue(this, "Jobs", {
      visibilityTimeout: cdk.Duration.minutes(16),
      retentionPeriod: cdk.Duration.days(4),
      enforceSSL: true,
      deadLetterQueue: { queue: deadLetterQueue, maxReceiveCount: 2 },
    });

    // ---- lambda assets --------------------------------------------------

    const appCode = lambda.Code.fromAsset(path.join(__dirname, "..", "build", "app"));

    const dependencies = new lambda.LayerVersion(this, "Dependencies", {
      code: lambda.Code.fromAsset(path.join(__dirname, "..", "build", "layer")),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      description: "pydantic, google-genai, clerk-backend-api, fastapi, mangum",
    });

    /** Explicit log groups: the deprecated `logRetention` prop provisions an extra
     * custom-resource Lambda just to call PutRetentionPolicy. */
    const logGroup = (id: string) =>
      new logs.LogGroup(this, id, {
        retention: logs.RetentionDays.TWO_WEEKS,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      });

    const commonEnvironment = {
      DDB_TABLE_NAME: table.tableName,
      S3_BUCKET_TRANSCRIPTS: transcripts.bucketName,
    };

    // ---- API ------------------------------------------------------------

    const api = new lambda.Function(this, "Api", {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "services.api.lambda_handler.handler",
      code: appCode,
      layers: [dependencies],
      memorySize: 512,
      timeout: cdk.Duration.seconds(30),
      logGroup: logGroup("ApiLogs"),
      environment: {
        ...commonEnvironment,
        SQS_QUEUE_URL: jobs.queueUrl,
        CORS_ALLOWED_ORIGINS: props.corsAllowedOrigins,
        CLERK_AUTHORIZED_PARTIES: props.corsAllowedOrigins,
        CLERK_SECRET_KEY_PARAM: CLERK_SECRET_PARAM,
      },
    });

    table.grantReadWriteData(api);
    transcripts.grantReadWrite(api);
    jobs.grantSendMessages(api);

    // ---- worker ---------------------------------------------------------

    const worker = new lambda.Function(this, "Worker", {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "services.worker.handler.handler",
      code: appCode,
      layers: [dependencies],
      memorySize: 1024,
      timeout: cdk.Duration.minutes(15),
      logGroup: logGroup("WorkerLogs"),
      environment: {
        ...commonEnvironment,
        LLM_PROVIDER: props.llmProvider,
        LLM_MODEL: props.llmModel,
        LLM_API_KEY_PARAM: LLM_API_KEY_PARAM,
      },
    });

    table.grantReadWriteData(worker);
    transcripts.grantRead(worker);

    // One message at a time: each job runs the full pipeline and holds the
    // invocation for minutes. Batching would only queue work behind a timeout.
    worker.addEventSource(new SqsEventSource(jobs, { batchSize: 1, reportBatchItemFailures: true }));

    // ---- secrets --------------------------------------------------------

    // CloudFormation cannot create SecureString parameters, so these are written
    // once with the CLI (see docs/despliegue-aws.md) and only read here.
    const parameterArn = cdk.Arn.format(
      { service: "ssm", resource: "parameter", resourceName: "po-agent/*" },
      this,
    );

    const readParameters = new iam.PolicyStatement({
      actions: ["ssm:GetParameter", "ssm:GetParameters"],
      resources: [parameterArn],
    });

    // Scoped to SSM: this grant cannot be used to decrypt anything else.
    const decryptViaSsm = new iam.PolicyStatement({
      actions: ["kms:Decrypt"],
      resources: ["*"],
      conditions: { StringEquals: { "kms:ViaService": `ssm.${this.region}.amazonaws.com` } },
    });

    for (const fn of [api, worker]) {
      fn.addToRolePolicy(readParameters);
      fn.addToRolePolicy(decryptViaSsm);
    }

    // ---- HTTP API -------------------------------------------------------

    // No CORS configured here on purpose: the FastAPI app owns CORS, and having
    // both answer preflight produces duplicate Access-Control-Allow-Origin
    // headers, which browsers reject.
    const httpApi = new HttpApi(this, "HttpApi", {
      description: "Agente PO API",
    });

    httpApi.addRoutes({
      path: "/{proxy+}",
      methods: [HttpMethod.ANY],
      integration: new HttpLambdaIntegration("ApiIntegration", api),
    });

    httpApi.addRoutes({
      path: "/",
      methods: [HttpMethod.ANY],
      integration: new HttpLambdaIntegration("ApiRootIntegration", api),
    });

    // ---- outputs --------------------------------------------------------

    new cdk.CfnOutput(this, "ApiUrl", {
      value: httpApi.apiEndpoint,
      description: "Pon esto en NEXT_PUBLIC_API_BASE_URL y redespliega el frontend",
    });
    new cdk.CfnOutput(this, "TableName", { value: table.tableName });
    new cdk.CfnOutput(this, "TranscriptsBucket", { value: transcripts.bucketName });
    new cdk.CfnOutput(this, "JobsQueueUrl", { value: jobs.queueUrl });
    new cdk.CfnOutput(this, "DlqUrl", { value: deadLetterQueue.queueUrl });
  }
}
