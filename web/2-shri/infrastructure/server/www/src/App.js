import React, { useState, useCallback, useEffect } from "react";
import { Form } from "./Form";
import { List } from "./List";
import { BuildDetails } from "./BuildDetails";
import "./App.module.css";
import { getBuildsList, getBuildDetails, startBuild } from "./api";

export function App() {
  const [isFormSending, setIsFormSending] = useState(false);
  const [formSubmitStatus, setFormSubmitStatus] = useState("");
  const [repo, setRepo] = useState("");
  const [commithash, setCommithash] = useState("");
  const [command, setCommand] = useState("");

  const [lastTimeUpdateRequired, setLastTimeUpdateRequired] = useState(
    Date.now()
  );
  const [page, setPage] = useState(1);
  const [pagesCount, setPagesCount] = useState(1);
  const [builds, setBuilds] = useState([]);

  const [buildDetails, setBuildDetails] = useState(null);
  const [openedId, setOpenedId] = useState(null);

  useEffect(() => {
    async function fetchData() {
      const list = await getBuildsList({ page });
      setPagesCount(list.pagesCount);
      setBuilds(list.builds);
    }
    fetchData().catch(console.error);
  }, [lastTimeUpdateRequired, page]);

  useEffect(() => {
    async function fetchData() {
      if (!openedId) {
        return;
      }
      const buildDetails = await getBuildDetails({ id: openedId });
      setBuildDetails(buildDetails);
    }
    fetchData().catch(console.error);
  }, [openedId]);

  const sendFormRequest = useCallback(async () => {
    if (isFormSending) {
      return;
    }
    setIsFormSending(true);
    setFormSubmitStatus("");

    await startBuild({ commithash, repo, command });
    setFormSubmitStatus("Задача успешно создана");

    setLastTimeUpdateRequired(Date.now());
    setIsFormSending(false);
    setCommithash("");
    setRepo("");
    setCommand("");
  }, [isFormSending, commithash, repo, command]);

  return (
    <>
      <h1>ШРИ CI</h1>
      {formSubmitStatus}
      <Form
        onSubmit={sendFormRequest}
        isDisabled={isFormSending}
        onRepoChange={setRepo}
        onCommithashChange={setCommithash}
        onCommandChange={setCommand}
        repo={repo}
        commithash={commithash}
        command={command}
      />
      <List
        builds={builds}
        page={page}
        pagesCount={pagesCount}
        onItemClick={setOpenedId}
        onPageChange={setPage}
      />
      {buildDetails && <BuildDetails {...buildDetails} />}
    </>
  );
}
