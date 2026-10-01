import Footer from "./components/Footer";
import Hero from "./components/Hero";
import Methodology from "./components/Methodology";
import Nav from "./components/Nav";
import CalibrationSection from "./components/sections/CalibrationSection";
import ChoiceSection from "./components/sections/ChoiceSection";
import FailuresSection from "./components/sections/FailuresSection";
import LatencySection from "./components/sections/LatencySection";
import SelectiveSection from "./components/sections/SelectiveSection";
import TakeawaysSection from "./components/sections/TakeawaysSection";

export default function App() {
  return (
    <>
      <Nav />
      <main className="wrap">
        <Hero />
        <Methodology />
        <ChoiceSection />
        <CalibrationSection />
        <SelectiveSection />
        <LatencySection />
        <FailuresSection />
        <TakeawaysSection />
        <Footer />
      </main>
    </>
  );
}
