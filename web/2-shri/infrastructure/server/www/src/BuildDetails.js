import React from "react";

export function BuildDetails({
  id,
  commithash,
  repo,
  buildstatus,
  exitcode,
  stdout,
  stderr,
  startdate,
  enddate,
  command
}) {
  return (
    <>
      <h3>Подробности сборки</h3>
      <div>id: {id}</div>
      <div>commithash: {commithash}</div>
      <div>repo: {repo}</div>
      <div>command: {command}</div>
      <div>buildstatus: {buildstatus}</div>
      <div>exitcode: {exitcode}</div>
      <div>stdout: {stdout}</div>
      <div>stderr: {stderr}</div>
      <div>startdate: {startdate}</div>
      <div>enddate: {enddate}</div>
    </>
  );
}
