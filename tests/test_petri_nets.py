# tests/test_petri_nets.py
import unittest
from dataclasses import dataclass

# Assuming llm_tap is installed or PYTHONPATH is set for tests
from llm_tap.petri_nets import Token, Place, Transition, PetriNet, InputTokenMap, ActionOutput

@dataclass
class SimpleColor:
    data: str

class TestPetriNets(unittest.TestCase):

    def test_token_creation_and_equality(self):
        token1 = Token(value="hello")
        token2 = Token(value="hello")
        token3 = Token(value="world")
        self.assertEqual(token1, token2)
        self.assertNotEqual(token1, token3)

        obj_color1 = SimpleColor(data="test")
        obj_color2 = SimpleColor(data="test")
        token_obj1 = Token(value=obj_color1)
        token_obj2 = Token(value=obj_color2) # Different obj, same value
        self.assertEqual(token_obj1, token_obj2)


    def test_place_add_remove_token(self):
        place = Place(name="TestPlace")
        token_a = Token(value="A")
        token_b = Token(value="B")

        place.add_token(token_a)
        self.assertIn(token_a, place.tokens)
        self.assertEqual(len(place.tokens), 1)

        place.add_token(token_b)
        self.assertIn(token_b, place.tokens)
        self.assertEqual(len(place.tokens), 2)

        place.remove_token(token_a)
        self.assertNotIn(token_a, place.tokens)
        self.assertEqual(len(place.tokens), 1)

        with self.assertRaises(ValueError):
            place.remove_token(Token(value="C")) # Token not present

    def test_transition_is_enabled(self):
        # Always true guard
        trans_true = Transition(name="T_True")
        self.assertTrue(trans_true.is_enabled({}))

        # Always false guard
        trans_false = Transition(name="T_False", guard=lambda inputs: False)
        self.assertFalse(trans_false.is_enabled({}))

        # Guard checking for specific token
        def specific_token_guard(inputs: InputTokenMap) -> bool:
            place_a_tokens = inputs.get("P_A", [])
            return any(token.value == "required_data" for token in place_a_tokens)

        trans_specific = Transition(name="T_Specific", guard=specific_token_guard, input_place_names=["P_A"])

        self.assertFalse(trans_specific.is_enabled({"P_A": []}))
        self.assertFalse(trans_specific.is_enabled({"P_A": [Token("other_data")]}))
        self.assertTrue(trans_specific.is_enabled({"P_A": [Token("required_data")]}))
        self.assertTrue(trans_specific.is_enabled({"P_A": [Token("other"), Token("required_data")]}))

    def test_petrinet_add_components(self):
        net = PetriNet(name="TestNet")
        p1 = Place(name="P1")
        t1 = Transition(name="T1")

        net.add_place(p1)
        self.assertIn("P1", net.places)
        net.add_transition(t1)
        self.assertIn("T1", net.transitions)

        with self.assertRaises(ValueError):
            net.add_place(Place(name="P1")) # Duplicate place name
        with self.assertRaises(ValueError):
            net.add_transition(Transition(name="T1")) # Duplicate transition name

    def test_petrinet_simple_fire_sequence(self):
        net = PetriNet(name="SimpleSequenceNet")

        p_start = Place(name="Start")
        p_end = Place(name="End")

        # Action: move one token from Start to End
        def move_action(inputs: InputTokenMap) -> ActionOutput:
            start_tokens = inputs.get("Start", [])
            if start_tokens:
                token_to_move = start_tokens[0]
                return {"Start": [token_to_move]}, {"End": [Token(value=token_to_move.value + "_moved")]}
            return {}, {}

        t_move = Transition(name="Move",
                                input_place_names=["Start"],
                                output_place_names=["End"],
                                action=move_action)

        net.add_place(p_start)
        net.add_place(p_end)
        net.add_transition(t_move)

        initial_token = Token(value="data")
        net.add_token("Start", initial_token)

        self.assertEqual(len(net.places["Start"].tokens), 1)
        self.assertEqual(len(net.places["End"].tokens), 0)

        enabled_trans = net.get_enabled_transitions()
        self.assertEqual(len(enabled_trans), 1)
        self.assertEqual(enabled_trans[0].name, "Move")

        fired = net.fire_transition("Move")
        self.assertTrue(fired)

        self.assertEqual(len(net.places["Start"].tokens), 0)
        self.assertEqual(len(net.places["End"].tokens), 1)
        self.assertEqual(net.places["End"].tokens[0].value, "data_moved")

        # No more enabled transitions
        self.assertEqual(len(net.get_enabled_transitions()), 0)

    def test_petrinet_run_simulation(self):
        net = PetriNet(name="RunNet")
        p1 = Place(name="P1")
        p2 = Place(name="P2")
        p3 = Place(name="P3")

        # T1: P1 -> P2
        def action_t1(inputs: InputTokenMap) -> ActionOutput:
            p1_tokens = inputs.get("P1", [])
            if p1_tokens:
                return {"P1": [p1_tokens[0]]}, {"P2": [Token(p1_tokens[0].value)]}
            return {}, {}
        t1 = Transition(name="T1", input_place_names=["P1"], output_place_names=["P2"], action=action_t1)

        # T2: P2 -> P3
        def action_t2(inputs: InputTokenMap) -> ActionOutput:
            p2_tokens = inputs.get("P2", [])
            if p2_tokens:
                return {"P2": [p2_tokens[0]]}, {"P3": [Token(p2_tokens[0].value)]}
            return {}, {}
        t2 = Transition(name="T2", input_place_names=["P2"], output_place_names=["P3"], action=action_t2)

        net.add_place(p1)
        net.add_place(p2)
        net.add_place(p3)
        net.add_transition(t1)
        net.add_transition(t2)

        net.add_token("P1", Token("A"))
        net.add_token("P1", Token("B"))

        steps = net.run()
        self.assertEqual(steps, 4) # T1 fires for A, T1 fires for B, T2 fires for A, T2 fires for B (or similar order)

        self.assertEqual(len(net.places["P1"].tokens), 0)
        self.assertEqual(len(net.places["P2"].tokens), 0)
        self.assertEqual(len(net.places["P3"].tokens), 2)
        self.assertIn(Token("A"), net.places["P3"].tokens)
        self.assertIn(Token("B"), net.places["P3"].tokens)


if __name__ == "__main__":
    unittest.main()
