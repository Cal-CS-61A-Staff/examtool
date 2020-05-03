import React from "react";
import { render } from "react-dom";
import StaffApp from "./StaffApp";

function init() {
    render(<StaffApp />, document.querySelector("#root"));
}

init();
