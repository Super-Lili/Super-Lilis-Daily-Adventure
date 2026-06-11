import unittest
from main import process

class TestKnowledgeCompass(unittest.TestCase):

    def test_valid_input_ai_creative_work(self):
        # Test with the specific topic that has predefined data
        topic = "人工智能与创意工作"
        result_html = process(topic)

        self.assertIsInstance(result_html, str)
        self.assertIn("<!DOCTYPE html>", result_html)
        self.assertIn("知识指南针：人工智能与创意工作 精选书单", result_html)
        self.assertIn("奠基之作</h3>", result_html)
        self.assertIn("人工智能：一种现代方法", result_html)
        self.assertIn("反叛视角</h3>", result_html)
        self.assertIn("李开复", result_html)
        self.assertIn("实践者之书</h3>", result_html)
        self.assertIn("历史与背景</h3>", result_html)
        self.assertIn("跨学科桥梁</h3>", result_html)
        self.assertIn("现在与未来</h3>", result_html)
        self.assertIn("A Thousand Brains:", result_html) # Check for a specific book from the future section

        # Verify the "为何阅读" and "视角" are present for at least one book
        self.assertIn("理解AI如何“思考”和“运作”的底层逻辑", result_html)
        self.assertIn("系统性阐述人工智能基础理论与方法", result_html)

    def test_other_topic_placeholder(self):
        # Test with a topic that should trigger the placeholder "待补充"
        topic = "慢媒体与注意力经济"
        result_html = process(topic)

        self.assertIsInstance(result_html, str)
        self.assertIn("<!DOCTYPE html>", result_html)
        self.assertIn("知识指南针：慢媒体与注意力经济 精选书单", result_html)
        self.assertIn("奠基之作</h3>", result_html)
        self.assertIn("此话题暂无预设书单", result_html)
        self.assertIn("placeholder-item", result_html)

    def test_empty_input(self):
        # Test with empty input
        result_html = process("")
        self.assertIsInstance(result_html, str)
        self.assertIn("错误提示", result_html)
        self.assertIn("提供的话题太短或为空", result_html)

    def test_short_input(self):
        # Test with very short input
        result_html = process("AI")
        self.assertIsInstance(result_html, str)
        self.assertIn("错误提示", result_html)
        self.assertIn("提供的话题太短或为空", result_html)

    def test_whitespace_input(self):
        # Test with only whitespace input
        result_html = process("   ")
        self.assertIsInstance(result_html, str)
        self.assertIn("错误提示", result_html)
        self.assertIn("提供的话题太短或为空", result_html)

if __name__ == '__main__':
    unittest.main()