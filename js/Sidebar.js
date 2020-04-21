import React from "react";
import { Nav } from "react-bootstrap";

export default function Sidebar({ groups }) {
    return (
        <Nav defaultActiveKey="/home" className="flex-column">
            {groups.map((group, i) => (
                <>
                    <Nav.Link href={`#${i}`}>
                        {i + 1}
                        {". "}
                        {group.name}
                    </Nav.Link>
                    {group.questions.map((question, j) => (
                        <Nav.Link style={{ paddingLeft: 20 }} href={`#${i}_${j}`}>
                            Q
                            {i + 1}
                            .
                            {j + 1}
                        </Nav.Link>
                    ))}
                </>
            ))}
        </Nav>
    );
}
