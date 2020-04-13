import React, { useState } from "react";
import {
    Col, Container, Form, Row,
} from "react-bootstrap";
import { auth2 } from "gapi";
import Exam from "./Exam";
import ExamContext from "./ExamContext";
import PasswordDecryptor from "./PasswordDecryptor";
import ExamDownloader from "./ExamDownloader";
import GoogleSignInButton from "./GoogleSignInButton";

export default function App() {
    const [username, setUsername] = useState(
        window.location.hostname === "localhost" ? "exam-test@berkeley.edu" : "",
    );

    const [selectedExam, setSelectedExam] = useState("");

    const [encryptedExam, setEncryptedExam] = useState(null);

    const [savedAnswers, setSavedAnswers] = useState(null);

    const [decryptedExam, setDecryptedExam] = useState(null);

    const logout = (e) => {
        e.preventDefault();
        setUsername("");
        auth2.getAuthInstance().signOut();
        window.location.reload();
    };

    const handleExamSelect = (e) => {
        setSelectedExam(e.target.value);
        setEncryptedExam(null);
    };

    const handleReceiveExam = ({ exam, payload, answers }) => {
        setSelectedExam(exam);
        setEncryptedExam(payload);
        setSavedAnswers(answers);
    };

    return (
        <Container>
            <br />
            <Row>
                <Col>
                    <h1>CS 61A Final Exam</h1>
                </Col>
            </Row>
            <Row>
                <Col>
                    {!username && (
                        <GoogleSignInButton onSuccess={(receivedUsername, receivedToken) => {
                            setUsername(receivedUsername);
                        }}
                        />
                    )}
                    {username && (
                        <>
                            You have signed in as
                            {" "}
                            <b>{username}</b>
                            .
                            {" "}
                            {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
                            <a href="#" onClick={logout}>Log out</a>
                            {" "}
                            if this is not the right account.
                        </>
                    )}
                </Col>
            </Row>
            {(username && !encryptedExam) && (
                <>
                    <br />
                    <Row>
                        <Col>
                            <Form>
                                <Form.Group controlId="exampleForm.SelectCustom">
                                    <Form.Label>Now, choose your exam:</Form.Label>
                                    <Form.Control
                                        as="select"
                                        value={selectedExam}
                                        onChange={handleExamSelect}
                                        custom
                                    >
                                        <option hidden disabled selected value="">Select an exam</option>
                                        <option>cs61a-exam-test</option>
                                        <option>cs61a-final-monday</option>
                                        <option>cs61a-final-wednesday</option>
                                        <option>cs61a-final-friday</option>
                                    </Form.Control>
                                </Form.Group>
                            </Form>
                        </Col>
                    </Row>
                </>
            )}
            {(selectedExam && !encryptedExam) && (
                <Row>
                    <Col>
                        <p>
                            You have selected the exam
                            {" "}
                            <b>{selectedExam}</b>
                            . If this does not look correct, please re-select your exam.
                        </p>
                        <p>
                            Otherwise, click the button to generate your exam.
                            You can do this before the exam starts.
                        </p>
                        <ExamDownloader
                            exam={selectedExam}
                            onReceive={handleReceiveExam}
                        />
                    </Col>
                </Row>
            )}
            {(encryptedExam && !decryptedExam) && (
                <>
                    <br />
                    <Row>
                        <Col>
                            <p>
                                The
                                {" "}
                                <b>{selectedExam}</b>
                                {" "}
                                exam has successfully been downloaded!
                                Enter the password distributed by course staff to decrypt it
                                and start the exam.
                            </p>
                            <PasswordDecryptor
                                encryptedExam={encryptedExam}
                                onDecrypt={setDecryptedExam}
                            />
                        </Col>
                    </Row>
                </>
            )}
            <br />
            <ExamContext.Provider value={{ exam: selectedExam, savedAnswers }}>
                {decryptedExam && <Exam exam={decryptedExam} />}
            </ExamContext.Provider>
        </Container>
    );
}
