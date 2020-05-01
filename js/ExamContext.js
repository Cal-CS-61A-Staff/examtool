import { createContext } from "react";

const ExamContext = createContext({ savedAnswers: {}, onInternetError: () => null });

export default ExamContext;
