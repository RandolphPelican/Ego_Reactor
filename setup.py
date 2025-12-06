from setuptools import setup, find_packages
setup(
    name="ego_reactor",
    version="0.1.0",
    description="Neuromorphic Event-Driven Swarm Intelligence",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
)
