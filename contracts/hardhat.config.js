require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: "../backend/.env" });

const PRIVATE_KEY = process.env.MONAD_PRIVATE_KEY || "0x0000000000000000000000000000000000000000000000000000000000000000";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.20",
  networks: {
    hardhat: {},
    monadTestnet: {
      url: "https://testnet-rpc.monad.xyz",
      accounts: PRIVATE_KEY !== "0x0000000000000000000000000000000000000000000000000000000000000000" ? [PRIVATE_KEY] : [],
      chainId: 10143
    }
  }
};
