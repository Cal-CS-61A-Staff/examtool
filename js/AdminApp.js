import React, { useState } from "react";
import {
    Col, Container, Row,
} from "react-bootstrap";
import GoogleSignInButton from "./GoogleSignInButton";

export default function AdminApp() {
    const [username, setUsername] = useState("");

    return (
        <Container>
            <br />
            <Row>
                <Col>
                    <h1>Final Exam</h1>
                </Col>
            </Row>
            <Row>
                <Col>
                    <GoogleSignInButton
                        onSuccess={setUsername}
                    />
                </Col>
            </Row>
        </Container>
    );
}
