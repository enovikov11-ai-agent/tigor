import React from "react";
import { Paginator } from "../Paginator";
import { action } from "@storybook/addon-actions";

export default {
  title: "Paginator",
  component: Paginator
};

export const little = () => (
  <>
    <Paginator pagesCount={1} page={1} onPageChange={action("pageChange")} />
    <Paginator pagesCount={3} page={1} onPageChange={action("pageChange")} />
    <Paginator pagesCount={3} page={2} onPageChange={action("pageChange")} />
    <Paginator pagesCount={3} page={3} onPageChange={action("pageChange")} />
  </>
);

export const normal = () => (
  <>
    <Paginator pagesCount={5} page={1} onPageChange={action("pageChange")} />
    <Paginator pagesCount={5} page={2} onPageChange={action("pageChange")} />
    <Paginator pagesCount={5} page={3} onPageChange={action("pageChange")} />
    <Paginator pagesCount={5} page={4} onPageChange={action("pageChange")} />
    <Paginator pagesCount={5} page={5} onPageChange={action("pageChange")} />
  </>
);

export const big = () => (
  <>
    <Paginator pagesCount={10} page={1} onPageChange={action("pageChange")} />
    <Paginator pagesCount={10} page={2} onPageChange={action("pageChange")} />
    <Paginator pagesCount={10} page={3} onPageChange={action("pageChange")} />
    <Paginator pagesCount={10} page={4} onPageChange={action("pageChange")} />
    <Paginator pagesCount={10} page={5} onPageChange={action("pageChange")} />
    <Paginator pagesCount={10} page={6} onPageChange={action("pageChange")} />
    <Paginator pagesCount={10} page={7} onPageChange={action("pageChange")} />
    <Paginator pagesCount={10} page={8} onPageChange={action("pageChange")} />
    <Paginator pagesCount={10} page={9} onPageChange={action("pageChange")} />
    <Paginator pagesCount={10} page={10} onPageChange={action("pageChange")} />
  </>
);
