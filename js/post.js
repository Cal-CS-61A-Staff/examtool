export default async function post(endpoint, data) {
    return timeoutPromise(10000, fetch(endpoint, {
        method: "POST",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    }));
}

function timeoutPromise(ms, promise) {
    return new Promise((resolve, reject) => {
        const timeoutId = setTimeout(() => {
            reject(new Error("promise timeout"));
        }, ms);
        promise.then(
            (res) => {
                clearTimeout(timeoutId);
                resolve(res);
            },
            (err) => {
                clearTimeout(timeoutId);
                reject(err);
            },
        );
    });
}
