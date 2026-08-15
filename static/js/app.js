/* =========================================================
   MHCORE
   Global Application JavaScript
========================================================= */

(function () {

    "use strict";


    /* =====================================================
       THEME MANAGEMENT
    ===================================================== */

    const html = document.documentElement;

    const toggle =
        document.getElementById("themeToggle") ||
        document.getElementById("appearanceToggle");

    const icon =
        document.getElementById("themeIcon") ||
        document.getElementById("appearanceIcon");


    /* =====================================================
       APPLY THEME
    ===================================================== */

    function applyTheme(theme) {

        html.setAttribute(
            "data-theme",
            theme
        );


        if (!toggle || !icon) {
            return;
        }


        if (theme === "dark") {

            /*
             * Show sun when currently in dark mode.
             * Clicking it switches to light mode.
             */

            icon.textContent = "☀";

            toggle.setAttribute(
                "aria-label",
                "Switch to light mode"
            );

            toggle.setAttribute(
                "title",
                "Switch to light mode"
            );

        } else {

            /*
             * Show moon when currently in light mode.
             * Clicking it switches to dark mode.
             */

            icon.textContent = "◐";

            toggle.setAttribute(
                "aria-label",
                "Switch to dark mode"
            );

            toggle.setAttribute(
                "title",
                "Switch to dark mode"
            );

        }

    }


    /* =====================================================
       GET INITIAL THEME
    ===================================================== */

    function getInitialTheme() {

        const savedTheme =
            localStorage.getItem(
                "mhcore-theme"
            );


        /*
         * If the user has already selected
         * a theme, always respect it.
         */

        if (
            savedTheme === "dark" ||
            savedTheme === "light"
        ) {

            return savedTheme;

        }


        /*
         * Otherwise follow the operating system.
         */

        const prefersDark =
            window.matchMedia(
                "(prefers-color-scheme: dark)"
            ).matches;


        return prefersDark
            ? "dark"
            : "light";

    }


    /* =====================================================
       APPLY INITIAL THEME
    ===================================================== */

    applyTheme(
        getInitialTheme()
    );


    /* =====================================================
       THEME TOGGLE
    ===================================================== */

    if (toggle) {

        toggle.addEventListener(
            "click",
            function () {

                const currentTheme =
                    html.getAttribute(
                        "data-theme"
                    );


                const newTheme =
                    currentTheme === "dark"
                        ? "light"
                        : "dark";


                /*
                 * Save user's preference.
                 */

                localStorage.setItem(
                    "mhcore-theme",
                    newTheme
                );


                /*
                 * Apply immediately.
                 */

                applyTheme(
                    newTheme
                );

            }
        );

    }


    /* =====================================================
       SYSTEM THEME CHANGES
    ===================================================== */

    const mediaQuery =
        window.matchMedia(
            "(prefers-color-scheme: dark)"
        );


    mediaQuery.addEventListener(
        "change",
        function (event) {

            /*
             * If the user manually selected
             * a theme, don't override it.
             */

            const savedTheme =
                localStorage.getItem(
                    "mhcore-theme"
                );


            if (savedTheme) {
                return;
            }


            applyTheme(
                event.matches
                    ? "dark"
                    : "light"
            );

        }
    );

})();