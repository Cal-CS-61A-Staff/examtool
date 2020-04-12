import React from "react";

export default function FailText({ text }) {
    return (
        <div style={{ color: "red" }}>
            {text}
            {" "}
            {text && "If this error persists, contact your course staff or use the alternative exam medium."}
        </div>
    );
}
