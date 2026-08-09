// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require("eslint-config-expo/flat");

module.exports = defineConfig([
  expoConfig,
  {
    ignores: ["dist/*", "dist-android/*"],
    rules: {
      // Các effect này khởi tạo dữ liệu từ Core API khi route/session thay đổi.
      "react-hooks/set-state-in-effect": "off",
    },
  }
]);
