import React from "react";
import { render } from "react-dom";
import App from "./App";

function init() {
    render(<App />, document.querySelector("#root"));
}

init();
