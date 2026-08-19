import React from "react";
import { Paginator } from "./Paginator";
import style from "./List.module.css";

export function List({ builds, page, pagesCount, onPageChange, onItemClick }) {
  const items = builds.map(({ id, commithash, repo, buildstatus }) => (
    <tr onClick={() => onItemClick(id)} className={style.item} key={id}>
      <td className={style.id}>{id}</td>
      <td>{commithash}</td>
      <td>{repo}</td>
      <td>{buildstatus}</td>
    </tr>
  ));
  return (
    <>
      <h3>Список билдов</h3>
      <table className={style.table}>
        <tbody>
          <tr>
            <th>id</th>
            <th>commithash</th>
            <th>repo</th>
            <th>buildstatus</th>
          </tr>
          {items}
        </tbody>
      </table>
      <Paginator
        pagesCount={pagesCount}
        page={page}
        onPageChange={onPageChange}
      />
    </>
  );
}
