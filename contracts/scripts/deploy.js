const hre = require("hardhat");

async function main() {
  console.log("Compiling and deploying CapsuleRegistry to Monad Testnet...");

  const CapsuleRegistry = await hre.ethers.getContractFactory("CapsuleRegistry");
  const registry = await CapsuleRegistry.deploy();

  await registry.waitForDeployment();

  console.log("--------------------------------------------------");
  console.log("CapsuleRegistry deployed successfully to Monad Testnet!");
  console.log("Contract Address:", await registry.getAddress());
  console.log("Chain ID: 10143");
  console.log("--------------------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
