deno run --allow-net --allow-write - <<'TS'
Deno.serve({ hostname: "0.0.0.0", port: 8000 }, async (req) => {
  const url = new URL(req.url);
  const name = decodeURIComponent(url.pathname.slice(1)).replaceAll("\\", "/").split("/").pop();

  if (req.method !== "PUT" || !name) {
    return new Response("use: curl -T file http://host:8000/file\n", { status: 400 });
  }

  await Deno.writeFile(name, req.body ?? new Uint8Array());
  return new Response(`uploaded: ${name}\n`, { status: 201 });
});
TS
