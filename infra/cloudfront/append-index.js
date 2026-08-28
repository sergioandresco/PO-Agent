// CloudFront Function (viewer-request) — resolucion de rutas para el export estatico.
//
// `next build` con output:"export" y trailingSlash:true produce un index.html por
// ruta: out/dashboard/index.html, out/sign-in/index.html, etc. S3 detras de un
// Origin Access Control NO agrega index.html automaticamente (eso solo lo hace el
// endpoint de website publico, que aqui no usamos porque el bucket es privado).
// Sin esta funcion, entrar directo a /dashboard devuelve 404 y el visitante cae en
// el fallback a la home, perdiendo el deep link.
//
// Coste: 2 millones de invocaciones al mes gratis, despues 0,10 USD por millon.
function handler(event) {
  var request = event.request;
  var uri = request.uri;

  if (uri.endsWith('/')) {
    // /dashboard/ -> /dashboard/index.html
    request.uri = uri + 'index.html';
  } else {
    var last = uri.substring(uri.lastIndexOf('/') + 1);
    if (last.indexOf('.') === -1) {
      // /dashboard -> /dashboard/index.html
      request.uri = uri + '/index.html';
    }
  }

  return request;
}
