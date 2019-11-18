const HtmlWebpackPlugin = require("html-webpack-plugin");
const path = require("path");

module.exports = {
    entry: "./src/index.jsx",
    output: {
    // path: __dirname + "/dist",
        path: "/Users/c/container/my_app/static/js/",
        filename: "index_bundle.js"
    },
    plugins: [
        new HtmlWebpackPlugin({ template: "./public/index.html" })
    ],
    module: {
        rules: [
            { test: /\.css$/, use: "css-loader" },
            { test: /\.(js|jsx)$/, exclude: /node_modules/, use: "babel-loader" }
        ]
    }
};
