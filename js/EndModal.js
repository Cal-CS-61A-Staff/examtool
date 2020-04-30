import React, { useState } from "react";
import { Modal } from "react-bootstrap";
import Button from "react-bootstrap/Button";

export default function EndModal() {
    const [visible, setVisible] = useState(true);

    return (
        <Modal show={visible} onHide={() => setVisible(false)}>
            <Modal.Header closeButton>
                <Modal.Title>The exam has ended!</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                You have 30 seconds to review your answers and ensure that they are saved.
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={() => setVisible(false)}>
                    Back to Exam
                </Button>
            </Modal.Footer>
        </Modal>

    );
}
