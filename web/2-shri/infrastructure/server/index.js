(async () => {
  const express = require("express");
  const app = express();

  const crypto = require("crypto");
  const secret = crypto.randomBytes(16).toString("hex");
  const host = process.env.HOST || "127.0.0.1";
  const port = process.env.PORT || 8080;
  const cookieParser = require("cookie-parser");

  const sqlite = require("sqlite");
  const db = await sqlite.open("./db.sqlite");
  await db.migrate({ force: "last" });

  app.use(cookieParser());
  app.use(express.static("./www/build"));
  app.use(express.urlencoded({ extended: true }));
  app.use(express.json());

  app.get("/login", (req, res) => {
    if (typeof req.query.secret === "string") {
      res.cookie("secret", req.query.secret);
      res.redirect("/");
    } else {
      res.send("bad secret");
    }
  });

  if (process.env.NODE_ENV !== "development") {
    app.use((req, res, next) => {
      if (req.cookies.secret !== secret) {
        res.send("bad secret");
      } else {
        next();
      }
    });
  } else {
    app.use((req, res, next) => {
      res.setHeader("Access-Control-Allow-Origin", "*");
      res.setHeader("Access-Control-Allow-Headers", "*");
      next();
    });
  }

  app.get("/v1/builds", async (req, res) => {
    const id = +req.query.id;
    const [build] = await db.all("SELECT * FROM Builds WHERE id = ?", id);
    res.json(build);
  });

  app.get("/v1/builds/list", async (req, res) => {
    const page = +req.query.page || 1;
    const countPerPage = 10;
    const builds = await db.all(
      "SELECT id, commithash, repo, buildstatus FROM Builds ORDER BY id ASC LIMIT ? OFFSET ?",
      countPerPage,
      (page - 1) * countPerPage
    );
    const countResult = await db.all("SELECT COUNT(*) FROM Builds");
    const pagesCount = Math.ceil(countResult[0]["COUNT(*)"] / countPerPage);
    res.json({ builds, pagesCount });
  });

  app.post("/v1/builds", async (req, res) => {
    await db.all(
      'INSERT INTO Builds (commithash, repo, buildstatus, exitcode, stdout, stderr, startdate, enddate, command) VALUES (?, ?, "WAIT", 0, "", "", ?, 0, ?)',
      req.body.commithash,
      req.body.repo,
      Math.floor(Date.now() / 1000),
      req.body.command
    );
    res.json({});
  });

  app.post("/v1/agents/new", async (req, res) => {
    await db.all(
      "INSERT INTO Agents (host, port, isbusy) VALUES (?, ?, false)",
      req.body.host,
      req.body.port
    );
    res.json({});
  });

  app.post("/v1/agents/update", async (req, res) => {});

  app.post("/v1/builds/update", async (req, res) => {
    //req.body : id, buildstatus, stdout, stderr
  });

  app.listen(port, host);
  console.log(`http://${host}:${port}/login?secret=${secret}`);
})();
