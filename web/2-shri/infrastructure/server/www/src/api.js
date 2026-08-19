async function get(url) {
  return fetch(url).then(res => res.json());
}

async function post(url, body) {
  return fetch(url, {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" }
  }).then(res => res.json());
}

const host =
  process.env.NODE_ENV === "development" ? "http://localhost:8080/" : "/";

export async function getBuildsList({ page }) {
  const data = await get(`${host}v1/builds/list?page=` + +page);
  return data;
}

export async function getBuildDetails({ id }) {
  const data = await get(`${host}v1/builds?id=` + +id);
  return data;
}

export async function startBuild({ commithash, repo, command }) {
  const data = await post(`${host}v1/builds`, { commithash, repo, command });
  return data;
}
