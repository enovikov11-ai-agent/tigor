import React from "react";
import { BuildDetails } from "../BuildDetails";

export default {
  title: "BuildDetails",
  component: BuildDetails
};

export const page = () => {
  const item = {
    id: 2,
    commithash: "hash",
    repo: "git",
    buildstatus: "WAIT",
    exitcode: 0,
    stdout: "",
    stderr: "",
    startdate: 1578773434,
    enddate: 0,
    command: "ls"
  };
  return <BuildDetails {...item} />;
};
