import React, { useEffect, useState } from "react";
import {
    Col, Container, Form, Navbar, Row,
} from "react-bootstrap";
import { auth2 } from "gapi";
import Exam from "./Exam";
import ExamContext from "./ExamContext";
import PasswordDecryptor from "./PasswordDecryptor";
import ExamDownloader from "./ExamDownloader";
import GoogleSignInButton from "./GoogleSignInButton";
import post from "./post";
import Timer from "./Timer";

export default function StudentApp() {
    const [username, setUsername] = useState(
        window.location.hostname === "localhost" ? "exam-test@berkeley.edu" : "",
    );

    const [examList, setExamList] = useState([]);

    const [selectedExam, setSelectedExam] = useState("");

    const [publicGroup, setPublicGroup] = useState(null);

    const [encryptedGroups, setEncryptedGroups] = useState(null);

    const [savedAnswers, setSavedAnswers] = useState(null);

    const [decryptedGroups, setDecryptedGroups] = useState(null);

    useEffect(() => {
        const go = async () => {
            setExamList(await (await post("list_exams")).json());
        };
        go();
    }, []);

    const logout = (e) => {
        e.preventDefault();
        setUsername("");
        auth2.getAuthInstance().signOut();
        window.location.reload();
    };

    const handleExamSelect = (e) => {
        setSelectedExam(e.target.value);
        setEncryptedGroups(null);
    };

    const handleReceiveExam = ({
        // eslint-disable-next-line no-shadow
        exam, publicGroup, privateGroups, answers,
    }) => {
        setSavedAnswers(answers);
        setSelectedExam(exam);
        setPublicGroup(publicGroup);
        setEncryptedGroups(privateGroups);
    };

    return (
        <>
            <Navbar bg="dark" variant="dark" sticky="top">
                <Navbar.Brand href="#">CS 61A Exam Runner</Navbar.Brand>
                <Timer target={1587495294} />
            </Navbar>
            <Container>
                <br />
                <Row>
                    <Col>
                        <h1>Final Exam</h1>
                    </Col>
                </Row>
                <Row>
                    <Col>
                        {!username && (
                            <GoogleSignInButton
                                onSuccess={(receivedUsername) => setUsername(receivedUsername)}
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
                {(username && !encryptedGroups) && (
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
                                            {examList.map((exam) => <option>{exam}</option>)}
                                        </Form.Control>
                                    </Form.Group>
                                </Form>
                            </Col>
                        </Row>
                    </>
                )}
                {(selectedExam && !encryptedGroups) && (
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
                {(encryptedGroups && !decryptedGroups) && (
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
                                    encryptedExam={encryptedGroups}
                                    onDecrypt={setDecryptedGroups}
                                />
                            </Col>
                        </Row>
                    </>
                )}
                <br />
                <ExamContext.Provider value={{ exam: selectedExam, savedAnswers }}>
                    <Exam publicGroup={publicGroup} groups={decryptedGroups} />
                </ExamContext.Provider>
            </Container>
        </>
    );
}
