const authorization = "Bearer " + JSON.parse(decodeURIComponent(document.cookie.split("; ").filter(e=>e.startsWith("__wtoken="))[0].substr(9))).accessToken,
    headers = { accept: "application/json", authorization }, latlon = "?lat=redacted&lon=redacted";

const restaurants = await fetch("https://consumer-api.wolt.com/v1/pages/restaurants" + latlon, {
  headers, mode: "cors", credentials: "include" }).then(res=>res.json());

const restorauntSlugs = [...new Set(restaurants.sections.map(e=>e.items || []).reduce((a,b)=>[...a,...b]).map(e=>e?.venue?.slug).filter(Boolean))];

const restorauntInfo = await fetch("https://consumer-api.wolt.com/v1/pages/venue-list/belgrade-milky" + latlon, {
  headers, mode: "cors", credentials: "include" }).then(res=>res.json());

