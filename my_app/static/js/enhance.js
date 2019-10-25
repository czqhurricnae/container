(function() {
    $("#the_tools-button").click(function(e) {
        // Fill the project tile automatically
        e.preventDefault();
        $("[id$='project_title']").text($("#title").val());
    });

    $("#title").on("change keyup paste", function() {
        // Change the project tile automatically
        $("[id$='project_title']").text($(this).val());
    });
})();
