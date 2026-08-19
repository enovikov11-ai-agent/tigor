import React from "react";

export function Form({
  onSubmit,
  isDisabled,
  repo,
  onRepoChange,
  commithash,
  onCommithashChange,
  command,
  onCommandChange
}) {
  return isDisabled ? (
    "Загрузка..."
  ) : (
    <form
      onSubmit={event => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div>
        Репозиторий:{" "}
        <input
          name="repo"
          value={repo}
          onChange={event => onRepoChange(event.target.value)}
        ></input>
      </div>
      <div>
        Комит для сборки:{" "}
        <input
          name="commithash"
          value={commithash}
          onChange={event => onCommithashChange(event.target.value)}
        ></input>
      </div>
      <div>
        Команда:{" "}
        <input
          name="command"
          value={command}
          onChange={event => onCommandChange(event.target.value)}
        ></input>
      </div>
      <button type="submit">Запустить сборку</button>
    </form>
  );
}
