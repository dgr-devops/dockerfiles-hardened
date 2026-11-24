"use strict";
const express = require("express");

const app = express();
app.disable("x-powered-by");

app.get("/", (_req, res) => res.json({ service: "node-demo", status: "ok" }));
app.get("/health", (_req, res) => res.json({ status: "healthy" }));

const port = Number(process.env.PORT || 3000);
app.listen(port, "0.0.0.0", () => console.log(`escuchando en ${port}`));
