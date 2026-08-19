import React from "react";
import { Form } from "../Form";

import { action } from "@storybook/addon-actions";

export default {
  title: "Form",
  component: Form
};

export const page = () => (
  <Form
    onSubmit={action("submit")}
    isDisabled={false}
    repo=""
    onRepoChange={action("repoChange")}
    commithash=""
    onCommithashChange={action("commithashChange")}
    command=""
    onCommandChange={action("commandChange")}
  />
);
