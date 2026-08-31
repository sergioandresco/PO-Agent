#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { PoAgentStack } from "../lib/po-agent-stack";

const app = new cdk.App();

/** Overridable at deploy time: `cdk deploy -c llmModel=gemini-2.5-pro`. */
function context(key: string): string {
  const value = app.node.tryGetContext(key);
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`Falta el contexto "${key}" — defínelo en cdk.json o pásalo con -c ${key}=...`);
  }
  return value;
}

new PoAgentStack(app, "PoAgentStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? "us-east-1",
  },
  corsAllowedOrigins: context("corsAllowedOrigins"),
  llmProvider: context("llmProvider"),
  llmModel: context("llmModel"),
  description: "Agente PO — backend fase 1 (API, cola, worker, DynamoDB, S3)",
});
