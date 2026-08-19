import React from "react";
import { List } from "../List";
import { action } from "@storybook/addon-actions";

export default {
  title: "List",
  component: List
};

export const withData = () => {
  const serverData = {
    builds: [
      { id: 11, commithash: "hash", repo: "git", buildstatus: 0 },
      { id: 12, commithash: "hash", repo: "git", buildstatus: 0 },
      { id: 13, commithash: "hash", repo: "git", buildstatus: 0 },
      { id: 14, commithash: "hash", repo: "git", buildstatus: 0 },
      { id: 15, commithash: "hash", repo: "git", buildstatus: 0 },
      { id: 16, commithash: "hash", repo: "git", buildstatus: 0 }
    ],
    pagesCount: 2
  };
  return (
    <List
      builds={serverData.builds}
      pagesCount={serverData.pagesCount}
      page={2}
      onPageChange={action("pageChange")}
      onItemClick={action("itemClick")}
    />
  );
};
