"""
Advanced Prompt Templates for TavilyAI Pro
Implements Chain-of-Thought, Tree-of-Thoughts, Self-Consistency, and Few-Shot prompting
"""

import json
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass


class PromptTechnique(Enum):
    """Available prompting techniques"""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    SELF_CONSISTENCY = "self_consistency"
    FEW_SHOT = "few_shot"
    REACT = "react"
    CONSTITUTIONAL_AI = "constitutional_ai"
    META_PROMPTING = "meta_prompting"


@dataclass
class PromptTemplate:
    """Template for a specific prompting technique"""
    technique: PromptTechnique
    template: str
    examples: Optional[List[Dict]] = None
    meta_instructions: Optional[str] = None


class PromptTemplateEngine:
    """
    Advanced prompt engineering with multiple techniques
    Generates optimal prompts based on task requirements
    """

    def __init__(self):
        self.templates = self._initialize_templates()
        self.few_shot_examples = self._initialize_few_shot_examples()

    def _initialize_templates(self) -> Dict[PromptTechnique, PromptTemplate]:
        """Initialize all prompt templates"""
        return {
            PromptTechnique.CHAIN_OF_THOUGHT: PromptTemplate(
                technique=PromptTechnique.CHAIN_OF_THOUGHT,
                template="""Let's approach this step-by-step:

Task: {task}

Please follow this structured thinking process:

1. **Understanding the Problem**
   - What is being asked?
   - What are the key components?
   - What constraints exist?

2. **Breaking Down the Problem**
   - Identify sub-problems
   - Determine dependencies
   - List required information

3. **Step-by-Step Analysis**
   {analysis_steps}

4. **Synthesis and Validation**
   - Combine insights from each step
   - Check for consistency
   - Validate against requirements

5. **Confidence Assessment**
   - Rate confidence (0-100%)
   - Identify uncertainties
   - Note assumptions made

6. **Final Answer**
   - Present clear conclusion
   - Include key supporting points
   - Provide confidence level

Let me work through this systematically:
""",
                meta_instructions="Think deeply and show your reasoning at each step."
            ),

            PromptTechnique.TREE_OF_THOUGHTS: PromptTemplate(
                technique=PromptTechnique.TREE_OF_THOUGHTS,
                template="""I'll explore multiple reasoning paths for this task:

Task: {task}

**Thought Tree Exploration:**

Path 1: {path1_description}
- Step 1.1: {reasoning}
- Step 1.2: {reasoning}
- Evaluation: {score}/10

Path 2: {path2_description}
- Step 2.1: {reasoning}
- Step 2.2: {reasoning}
- Evaluation: {score}/10

Path 3: {path3_description}
- Step 3.1: {reasoning}
- Step 3.2: {reasoning}
- Evaluation: {score}/10

**Path Selection:**
Based on evaluation, the most promising path is...

**Deep Dive on Selected Path:**
{detailed_exploration}

**Final Solution:**
{solution}

Confidence: {confidence}%
""",
                meta_instructions="Explore at least 3 different approaches before selecting the best."
            ),

            PromptTechnique.SELF_CONSISTENCY: PromptTemplate(
                technique=PromptTechnique.SELF_CONSISTENCY,
                template="""I'll solve this problem multiple times to ensure consistency:

Task: {task}

**Approach 1: {method1}**
{solution1}
Result: {result1}

**Approach 2: {method2}**
{solution2}
Result: {result2}

**Approach 3: {method3}**
{solution3}
Result: {result3}

**Consistency Check:**
- Do all approaches agree? {agreement}
- If not, why do they differ? {differences}
- Which approach is most reliable? {best_approach}

**Consolidated Answer:**
{final_answer}

Confidence based on consistency: {confidence}%
""",
                meta_instructions="Solve independently three times, then check for agreement."
            ),

            PromptTechnique.FEW_SHOT: PromptTemplate(
                technique=PromptTechnique.FEW_SHOT,
                template="""Here are some examples of similar tasks and their solutions:

{examples}

Now, let's apply the same approach to your task:

Task: {task}

Following the pattern from the examples:
{solution}

Key similarities to examples:
{similarities}

Key differences requiring adaptation:
{differences}

Final Answer: {answer}
""",
                meta_instructions="Learn from examples and apply the pattern."
            ),

            PromptTechnique.REACT: PromptTemplate(
                technique=PromptTechnique.REACT,
                template="""I'll use the ReAct (Reasoning + Acting) approach:

Task: {task}

**Thought 1:** {initial_thought}
**Action 1:** {action1}
**Observation 1:** {observation1}

**Thought 2:** Based on the observation, {thought2}
**Action 2:** {action2}
**Observation 2:** {observation2}

**Thought 3:** {thought3}
**Action 3:** {action3}
**Observation 3:** {observation3}

**Final Thought:** Combining all observations, {final_thought}

**Conclusion:** {conclusion}

Tools used: {tools_used}
Confidence: {confidence}%
""",
                meta_instructions="Alternate between thinking and acting with tools."
            ),

            PromptTechnique.CONSTITUTIONAL_AI: PromptTemplate(
                technique=PromptTechnique.CONSTITUTIONAL_AI,
                template="""I'll provide a response following these principles:

**Constitutional Principles:**
1. Accuracy: Ensure factual correctness
2. Helpfulness: Provide useful, actionable information
3. Harmlessness: Avoid potential negative impacts
4. Transparency: Be clear about limitations and assumptions
5. Objectivity: Present balanced, unbiased analysis

Task: {task}

**Initial Response:**
{initial_response}

**Constitutional Review:**
✓ Accuracy Check: {accuracy_check}
✓ Helpfulness Check: {helpfulness_check}
✓ Harmlessness Check: {harmlessness_check}
✓ Transparency Check: {transparency_check}
✓ Objectivity Check: {objectivity_check}

**Refined Response:**
{refined_response}

**Confidence:** {confidence}%
**Limitations:** {limitations}
""",
                meta_instructions="Self-critique and refine based on constitutional principles."
            ),

            PromptTechnique.META_PROMPTING: PromptTemplate(
                technique=PromptTechnique.META_PROMPTING,
                template="""**Meta-Analysis of Task:**

Task Type: {task_type}
Complexity: {complexity}
Domain: {domain}
Required Expertise: {expertise}

**Optimal Approach Selection:**
Given the task characteristics, the best approach is: {selected_approach}
Reasoning: {approach_reasoning}

**Customized Strategy:**
{custom_strategy}

**Execution:**
{execution}

**Meta-Reflection:**
- Was the approach selection correct? {reflection}
- What could be improved? {improvements}
- Confidence in result: {confidence}%

**Final Output:**
{final_output}
""",
                meta_instructions="Analyze the task itself before solving it."
            )
        }

    def _initialize_few_shot_examples(self) -> Dict[str, List[Dict]]:
        """Initialize few-shot examples for different domains"""
        return {
            "stock_analysis": [
                {
                    "question": "Should I invest in NVDA?",
                    "analysis": "1. Financial health: Strong revenue growth (101% YoY)\n"
                               "2. Market position: Leader in AI chips\n"
                               "3. Risks: High valuation, competition\n"
                               "4. Technical: Bullish trend, RSI 65",
                    "conclusion": "Bullish outlook with caution on valuation",
                    "confidence": 75
                },
                {
                    "question": "What's the outlook for AAPL?",
                    "analysis": "1. Financial: Stable revenue, high margins\n"
                               "2. Products: iPhone demand steady\n"
                               "3. Services: Growing segment\n"
                               "4. Technical: Support at $170",
                    "conclusion": "Moderate bullish, good for long-term",
                    "confidence": 80
                }
            ],
            "market_research": [
                {
                    "question": "How is the EV market evolving?",
                    "analysis": "1. Growth: 35% CAGR expected\n"
                               "2. Leaders: Tesla, BYD, traditional OEMs\n"
                               "3. Challenges: Charging infrastructure\n"
                               "4. Trends: Autonomous driving integration",
                    "conclusion": "Rapid growth with consolidation ahead",
                    "confidence": 85
                }
            ],
            "competitive_analysis": [
                {
                    "question": "How does Microsoft compete with Google in cloud?",
                    "analysis": "1. Market share: Azure 23%, GCP 10%\n"
                               "2. Strengths: Azure - enterprise, GCP - AI/ML\n"
                               "3. Pricing: Competitive, Azure slightly higher\n"
                               "4. Growth: Both growing, Azure faster adoption",
                    "conclusion": "Azure leading in enterprise, GCP in innovation",
                    "confidence": 90
                }
            ]
        }

    def generate_prompt(self,
                       task: str,
                       technique: PromptTechnique = PromptTechnique.CHAIN_OF_THOUGHT,
                       context: Optional[Dict[str, Any]] = None,
                       examples_domain: Optional[str] = None) -> str:
        """
        Generate an optimized prompt using the specified technique

        Args:
            task: The task description
            technique: The prompting technique to use
            context: Additional context for the prompt
            examples_domain: Domain for few-shot examples

        Returns:
            Generated prompt string
        """
        template = self.templates.get(technique)
        if not template:
            raise ValueError(f"Unknown technique: {technique}")

        # Prepare variables for template
        variables = {
            "task": task,
            "analysis_steps": self._generate_analysis_steps(task, context),
            "path1_description": "Direct financial analysis",
            "path2_description": "Market-based comparison",
            "path3_description": "Technical indicators approach",
            "method1": "Fundamental analysis",
            "method2": "Technical analysis",
            "method3": "Sentiment analysis",
            "confidence": 0,  # To be filled by model
            "examples": ""
        }

        # Add few-shot examples if requested
        if technique == PromptTechnique.FEW_SHOT and examples_domain:
            examples = self.few_shot_examples.get(examples_domain, [])
            if examples:
                examples_text = self._format_examples(examples)
                variables["examples"] = examples_text

        # Add context if provided
        if context:
            variables.update(context)

        # Format the template
        prompt = template.template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        # Add meta instructions if available
        if template.meta_instructions:
            prompt = f"[META: {template.meta_instructions}]\n\n{prompt}"

        return prompt

    def _generate_analysis_steps(self, task: str, context: Optional[Dict]) -> str:
        """Generate specific analysis steps based on task"""
        steps = []

        if "stock" in task.lower() or "invest" in task.lower():
            steps = [
                "Step 1: Analyze company financials (revenue, profit, debt)",
                "Step 2: Evaluate market position and competition",
                "Step 3: Review recent news and sentiment",
                "Step 4: Check technical indicators and trends",
                "Step 5: Assess risks and opportunities"
            ]
        elif "market" in task.lower():
            steps = [
                "Step 1: Identify market size and growth rate",
                "Step 2: Analyze key players and market share",
                "Step 3: Review industry trends and drivers",
                "Step 4: Assess regulatory environment",
                "Step 5: Project future scenarios"
            ]
        else:
            steps = [
                "Step 1: Define the core problem",
                "Step 2: Gather relevant information",
                "Step 3: Analyze key factors",
                "Step 4: Evaluate alternatives",
                "Step 5: Formulate recommendation"
            ]

        return "\n   ".join(steps)

    def _format_examples(self, examples: List[Dict]) -> str:
        """Format few-shot examples for prompt"""
        formatted = []
        for i, example in enumerate(examples, 1):
            formatted.append(f"""Example {i}:
Question: {example['question']}
Analysis: {example['analysis']}
Conclusion: {example['conclusion']}
Confidence: {example['confidence']}%
---""")
        return "\n\n".join(formatted)

    def select_optimal_technique(self, task: str, requirements: Dict[str, Any]) -> PromptTechnique:
        """
        Automatically select the best prompting technique for a task

        Args:
            task: Task description
            requirements: Task requirements (complexity, domain, etc.)

        Returns:
            Optimal PromptTechnique
        """
        task_lower = task.lower()
        complexity = requirements.get("complexity", 0.5)
        needs_reasoning = requirements.get("needs_reasoning", False)
        needs_consistency = requirements.get("needs_consistency", False)
        has_examples = requirements.get("has_examples", False)
        needs_tools = requirements.get("needs_tools", False)

        # Decision logic
        if needs_tools:
            return PromptTechnique.REACT
        elif needs_consistency or "verify" in task_lower:
            return PromptTechnique.SELF_CONSISTENCY
        elif has_examples:
            return PromptTechnique.FEW_SHOT
        elif complexity > 0.8:
            return PromptTechnique.TREE_OF_THOUGHTS
        elif needs_reasoning or complexity > 0.5:
            return PromptTechnique.CHAIN_OF_THOUGHT
        elif "principle" in task_lower or "ethical" in task_lower:
            return PromptTechnique.CONSTITUTIONAL_AI
        else:
            return PromptTechnique.CHAIN_OF_THOUGHT  # Default

    def enhance_with_meta_instructions(self, prompt: str, meta_requirements: Dict[str, Any]) -> str:
        """
        Add meta-level instructions to any prompt

        Args:
            prompt: Base prompt
            meta_requirements: Meta requirements (confidence, citations, etc.)

        Returns:
            Enhanced prompt with meta instructions
        """
        meta_parts = []

        if meta_requirements.get("require_confidence"):
            meta_parts.append("Provide confidence score (0-100%) for your answer")

        if meta_requirements.get("require_citations"):
            meta_parts.append("Cite sources for all factual claims")

        if meta_requirements.get("require_alternatives"):
            meta_parts.append("Consider alternative viewpoints")

        if meta_requirements.get("require_limitations"):
            meta_parts.append("Explicitly state limitations and assumptions")

        if meta_requirements.get("max_length"):
            meta_parts.append(f"Keep response under {meta_requirements['max_length']} words")

        if meta_parts:
            meta_instruction = "\n".join([f"• {part}" for part in meta_parts])
            return f"""[Requirements:
{meta_instruction}]

{prompt}"""
        return prompt

    def create_agent_specific_prompt(self, agent_role: str, task: str) -> str:
        """
        Create role-specific prompts for different agents

        Args:
            agent_role: Role of the agent (CEO, Research, Analysis, etc.)
            task: Task description

        Returns:
            Role-optimized prompt
        """
        role_prompts = {
            "CEO": """As the CEO Orchestrator, you are responsible for:
1. Strategic planning and task delegation
2. High-level decision making
3. Quality assurance of outputs
4. Resource allocation

Your approach should be strategic, comprehensive, and decisive.

Task: {task}

Provide executive-level analysis and delegation strategy:
""",
            "Research": """As the Research Division Leader, you specialize in:
1. Information gathering from multiple sources
2. Data verification and fact-checking
3. Identifying relevant trends and patterns
4. Synthesizing research findings

Your approach should be thorough, objective, and evidence-based.

Task: {task}

Conduct comprehensive research and provide findings:
""",
            "Analysis": """As the Analysis Division Leader, you excel at:
1. Deep analytical thinking
2. Statistical and financial analysis
3. Risk assessment and modeling
4. Creating actionable insights

Your approach should be rigorous, quantitative, and insightful.

Task: {task}

Perform detailed analysis and provide insights:
""",
            "Strategy": """As the Strategy Division Leader, you focus on:
1. Long-term planning and positioning
2. Competitive advantage identification
3. Opportunity assessment
4. Strategic recommendations

Your approach should be forward-thinking, creative, and pragmatic.

Task: {task}

Develop strategic recommendations:
"""
        }

        template = role_prompts.get(agent_role, role_prompts["Research"])
        return template.replace("{task}", task)

    def create_validation_prompt(self, original_task: str, response: str) -> str:
        """
        Create a prompt to validate and improve a response

        Args:
            original_task: Original task
            response: Response to validate

        Returns:
            Validation prompt
        """
        return f"""Please validate and potentially improve this response:

Original Task: {original_task}

Response to Validate:
{response}

Validation Criteria:
1. **Accuracy**: Are all facts correct?
2. **Completeness**: Are all aspects of the task addressed?
3. **Clarity**: Is the response clear and well-structured?
4. **Evidence**: Are claims properly supported?
5. **Objectivity**: Is the analysis balanced?

If any issues are found, provide an improved version.
Otherwise, confirm the response is satisfactory.

Validation Result:
"""

    def create_synthesis_prompt(self, responses: List[str], task: str) -> str:
        """
        Create a prompt to synthesize multiple responses

        Args:
            responses: List of responses to synthesize
            task: Original task

        Returns:
            Synthesis prompt
        """
        responses_text = "\n\n".join([f"Response {i+1}:\n{r}" for i, r in enumerate(responses)])

        return f"""Synthesize these multiple perspectives into a comprehensive answer:

Original Task: {task}

{responses_text}

Create a unified response that:
1. Combines the strongest points from each response
2. Resolves any contradictions
3. Provides a balanced, comprehensive answer
4. Maintains high confidence where responses agree
5. Notes areas of uncertainty where they disagree

Synthesized Response:
"""