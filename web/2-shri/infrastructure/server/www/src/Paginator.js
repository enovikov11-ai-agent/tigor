import React from "react";
import style from "./Paginator.module.css";
import cn from "classnames";

export function Paginator({ pagesCount, page, onPageChange }) {
  let min = page;
  let max = page;
  for (let i = 0; i < Math.min(6, pagesCount - 1); i++) {
    const fromLeft = min > 1 && (i % 2 === 0 || max === pagesCount);
    if (fromLeft) {
      min--;
    } else {
      max++;
    }
  }

  const items = [];
  for (let i = min; i <= max; i++) {
    items.push(
      <button
        onClick={() => onPageChange(i)}
        className={cn(style[page === i ? "active" : "inactive"], style.page)}
        key={i}
      >
        {i}
      </button>
    );
  }

  return <div>{items}</div>;
}
