"use strict";
// Comprobación de salud sin shell ni curl (la imagen final es distroless).
const http = require("http");

http
  .get("http://127.0.0.1:3000/health", { timeout: 2000 }, (res) => {
    process.exit(res.statusCode === 200 ? 0 : 1);
  })
  .on("error", () => process.exit(1))
  .on("timeout", () => process.exit(1));
