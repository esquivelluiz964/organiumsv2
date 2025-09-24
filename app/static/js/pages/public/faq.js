document.addEventListener("DOMContentLoaded", function () {
  const items = document.querySelectorAll(".faq-item");

  items.forEach(item => {
    const question = item.querySelector(".faq-question");
    const answer = item.querySelector(".faq-answer");

    question.addEventListener("click", () => {
      const isOpen = answer.style.display === "block";
      // Fecha todos
      document.querySelectorAll(".faq-answer").forEach(a => a.style.display = "none");
      // Alterna o clique atual
      answer.style.display = isOpen ? "none" : "block";
    });
  });
});
