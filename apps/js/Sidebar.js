import React from "react";
import { Nav } from "react-bootstrap";

export default function Sidebar({ groups }) {
    return (
        <Nav defaultActiveKey="/home" className="flex-column">
            {groups.map((group, i) => (
                <>
                    <Nav.Link href={`#${i + 1}`}>
                        {i + 1}
                        {". "}
                        {group.name}
                    </Nav.Link>
                    {group.elements.map((question, j) => (
                        <Nav.Link style={{ paddingLeft: 20 }} href={`#${i + 1}.${j + 1}`}>
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
