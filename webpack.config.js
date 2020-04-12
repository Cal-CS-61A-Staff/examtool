const path = require("path");

module.exports = {
    entry: "./js/index.js",
    watch: true,
    output: {
        filename: "main.js",
        path: path.resolve(__dirname, "static"),
    },
    externals: {
        react: "React",
        "react-dom": "ReactDOM",
        "react-bootstrap": "ReactBootstrap",
        gapi: "gapi",
        fernet: "fernet",
        MathJax: "MathJax"
    },
    module: {
        rules: [
            {
                test: /.jsx?$/,
                loader: "babel-loader",
                exclude: /node_modules/,
                query: {
                    presets: ["@babel/react"],
                },
            },
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: "eslint-loader",
                options: {
                    emitError: false,
                    emitWarning: true,
                },
            },
        ],
    },
};
