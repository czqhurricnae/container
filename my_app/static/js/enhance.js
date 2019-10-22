(function() {
    $("#the_tools-button").on("click", function() {
        // Fill the project tile automatically
        $("[id$='project_title']").text($("#title").text());
    });

    $("#title").on("change keyup paste", function() {
        // Change the project tile automatically
        $("[id$='project_title']").text($(this).val());
    });
})();
