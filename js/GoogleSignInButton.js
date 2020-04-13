import React, { useEffect } from "react";
// noinspection NpmUsedModulesInstalled
import { signin2 } from "gapi";

export default function GoogleSignInButton({ onSuccess }) {
    useEffect(() => {
        signin2.render("signInButton",
            {
                width: 200,
                longtitle: true,
                onSuccess: (user) => {
                    onSuccess(
                        user.getBasicProfile().getEmail(),
                    );
                },
            });
    }, []);
    return (
        <>
            First, sign into Google.
            <div
                id="signInButton"
                className="g-signin2"
                data-onsuccess="onSignIn"
                data-theme="dark"
            />
        </>
    );
}
