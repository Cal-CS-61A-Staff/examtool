import React, {
    useContext, useLayoutEffect, useRef, useState,
} from "react";
import { Form, FormControl, InputGroup } from "react-bootstrap";
import { getToken } from "./auth";
import ExamContext from "./ExamContext";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";
import Points from "./Points";
import post from "./post";

export default function Question({
    question, i, j,
}) {
    const examContext = useContext(ExamContext);

    const defaultValue = examContext.savedAnswers[question.id] || "";

    const [value, setValue] = useState(defaultValue);
    const [savedValue, setSavedValue] = useState(defaultValue);
    const [saving, setSaving] = useState(false);
    const [failText, setFailText] = useState("");

    const moveCursor = useRef(null);

    useLayoutEffect(() => {
        if (moveCursor.current !== null) {
            const { target, pos } = moveCursor.current;
            target.selectionStart = pos;
            target.selectionEnd = pos;
            moveCursor.current = null;
        }
    }, [moveCursor.current]);

    let contents;
    if (question.type === "multiple_choice") {
        contents = (
            <div style={{ marginBottom: 10 }}>
                {question.options.map((option) => (
                    <Form.Check
                        custom
                        checked={value === option}
                        name={question.id}
                        type="radio"
                        label={<span dangerouslySetInnerHTML={{ __html: option }} />}
                        value={option}
                        id={`${question.id}|${option}`}
                        onChange={(e) => { setValue(e.target.value); }}
                    />
                ))}
            </div>
        );
    } else if (question.type === "short_answer") {
        contents = (
            <InputGroup className="mb-3">
                <FormControl value={value} onChange={(e) => { setValue(e.target.value); }} />
            </InputGroup>
        );
    } else if (question.type === "short_code_answer") {
        contents = (
            <InputGroup className="mb-3">
                <FormControl
                    style={{ fontFamily: "monospace" }}
                    value={value}
                    onChange={(e) => {
                        setValue(e.target.value);
                    }}
                />
            </InputGroup>
        );
    } else if (question.type === "long_answer") {
        contents = (
            <InputGroup className="mb-3">
                <FormControl
                    as="textarea"
                    value={value}
                    rows={question.options}
                    onChange={(e) => {
                        setValue(e.target.value);
                    }}
                />
            </InputGroup>
        );
    } else if (question.type === "long_code_answer") {
        const tabHandler = (e) => {
            if (e.keyCode === 9) {
                e.preventDefault();
                const { target } = e;
                const start = target.selectionStart;
                const end = target.selectionEnd;
                setValue(`${value.substring(0, start)}\t${value.substring(end)}`);
                moveCursor.current = { target, pos: target.selectionStart + 1 };
            }
        };
        contents = (
            <InputGroup className="mb-3">
                <FormControl
                    as="textarea"
                    style={{ fontFamily: "\"Lucida Console\", Monaco, monospace", tabSize: 4 }}
                    value={value}
                    onKeyDown={tabHandler}
                    rows={question.options}
                    onChange={(e) => {
                        setValue(e.target.value);
                    }}
                />
            </InputGroup>
        );
    }

    const submit = async () => {
        setSaving(true);
        const ret = await post("submit_question", {
            id: question.id,
            value,
            token: getToken(),
            exam: examContext.exam,
        });
        setSaving(false);
        if (!ret.ok) {
            setFailText("Server failed to respond, please try again.");
        }
        try {
            const data = await ret.json();
            if (!data.success) {
                setFailText("Server responded but failed to save, please refresh and try again.");
            }
            setSavedValue(value);
            setFailText("");
        } catch {
            setFailText("Server returned invalid JSON. Please try again.");
        }
    };

    return (
        <>
            <Form>
                <Form.Label>
                    <h5 style={{ marginTop: 8, marginBottom: 0 }}>
                        Q
                        {i + 1}
                        .
                        {j + 1}
                    </h5>
                    {" "}
                    <Points
                        points={question.points}
                    />
                    <div
                        style={{ marginTop: 8 }}
                        dangerouslySetInnerHTML={{ __html: question.html }}
                    />
                </Form.Label>
                {contents}
                <LoadingButton
                    loading={saving}
                    disabled={saving || (value === savedValue)}
                    onClick={submit}
                >
                    {/* eslint-disable-next-line no-nested-ternary */}
                    {(value === savedValue) ? "Saved" : saving ? "Saving..." : "Save"}
                </LoadingButton>
                <FailText text={failText} />
            </Form>
            <br />
        </>
    );
}
