import React, { useEffect } from "react";
import { typeset } from "MathJax";
import { Col, Jumbotron, Row } from "react-bootstrap";
import Anchor from "./Anchor";
import Points from "./Points";
import Question from "./Question";
import Sidebar from "./Sidebar";

export default function Exam({ groups, publicGroup, ended }) {
    useEffect(() => typeset(), [groups]);

    const stickyStyle = {
        position: "sticky",
        top: "5em",
        height: "85vh",
        overflowY: "auto",
    };

    return (
        <div className="exam">
            <Row>
                <Col md={9} sm={12}>
                    {!ended && publicGroup && <Group group={publicGroup} i={-1} />}
                    {!ended && groups && groups.map((group, i) => <Group group={group} i={i} />)}
                    {groups && (
                        <Jumbotron>
                            {/* eslint-disable-next-line jsx-a11y/accessible-emoji */}
                            <h1>🎉Congratulations!🎉</h1>
                            <p>
                                You have reached the end of the exam!
                                Your answers will all be automatically saved.
                            </p>
                        </Jumbotron>
                    )}
                </Col>
                {!ended && groups && !!groups.length && (
                    <Col md={3} className="d-none d-md-block" style={stickyStyle}>
                        <Sidebar groups={groups} />
                    </Col>
                )}
            </Row>
        </div>
    );
}

function Group({ group, i }) {
    return (
        <>
            <div>
                <Anchor name={i} />
                <h3 style={{ marginBottom: 0 }}>
                    <b>
                        Q
                        {i + 1}
                    </b>
                    {" "}
                    {group.name}
                </h3>
                <Points
                    points={group.points}
                />
                {/* eslint-disable-next-line react/no-danger */}
                <div dangerouslySetInnerHTML={{ __html: group.html }} />
                { group.questions.map((question, j) => (
                    <Question question={question} i={i} j={j} />))}
            </div>
            <hr />
            <br />
        </>
    );
}
