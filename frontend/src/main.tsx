import React from "react";
import ReactDOM from "react-dom/client";
import {QueryClient, QueryClientProvider} from "@tanstack/react-query";
import {BrowserRouter} from "react-router-dom";
import App from "./App";
import ShowcaseStudio from "./ShowcaseStudio";
import "./styles.css";

const showcaseMode = import.meta.env.DEV ? new URLSearchParams(location.search).get("showcase") : null;

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><QueryClientProvider client={new QueryClient()}><BrowserRouter>{showcaseMode ? <ShowcaseStudio mode={showcaseMode}/> : <App />}</BrowserRouter></QueryClientProvider></React.StrictMode>
);
