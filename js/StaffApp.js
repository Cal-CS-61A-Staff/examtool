import React, { useEffect, useRef, useState } from "react";
import {
    Col, Container, Row,
} from "react-bootstrap";

import { edit } from "ace";
import Exam from "./Exam";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";
import post from "./post";

import sampleExam from "./sampleExam.md";

export default function StaffApp() {
    const [exam, setExam] = useState(null);
    const [failText, setFailText] = useState("");
    const [loading, setLoading] = useState(false);

    const editorRef = useRef();

    useEffect(() => {
        editorRef.current = edit("editor");
        editorRef.current.session.setMode("ace/mode/markdown");
        editorRef.current.setValue(sampleExam);
    }, []);

    const generate = async () => {
        const text = editorRef.current.getValue();
        setLoading(true);
        const ret = await post("convert", { text });
        setLoading(false);
        if (!ret.ok) {
            return;
        }
        const { success, examJSON, error } = await ret.json();
        if (success) {
            setExam(JSON.parse(examJSON));
            setFailText("");
        } else {
            setExam(null);
            setFailText(error);
        }
    };

    return (
        <Container fluid>
            <br />
            <Row>
                <Col>
                    <h1>Exam Generator</h1>
                    <div id="editor" style={{ width: "100%", height: 1000 }} />
                </Col>
                <Col>
                    <LoadingButton primary onClick={generate} loading={loading} disabled={loading}>
                        Generate
                    </LoadingButton>
                    <FailText text={failText} />
                    <br />
                    <div style={{
                        height: 900,
                        overflow: "auto",
                        border: "2px solid black",
                        padding: 10,
                    }}
                    >
                        {exam && <Exam exam={exam} />}
                    </div>
                </Col>
            </Row>
        </Container>
    );
}
