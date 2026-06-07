// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CapsuleRegistry {
    struct CapsuleRecord {
        string capsuleId;
        string title;
        bytes32 summaryHash;
        uint256 timestamp;
        address owner;
    }

    // Maps a capsule hash (keccak256 of capsule ID) to its registry record
    mapping(bytes32 => CapsuleRecord) private _registry;
    
    // List of all registered capsule hashes
    bytes32[] private _allCapsuleHashes;

    event CapsuleRegistered(
        bytes32 indexed key,
        string capsuleId,
        string title,
        bytes32 summaryHash,
        address indexed owner,
        uint256 timestamp
    );

    /**
     * @dev Register a new capsule summary on-chain.
     * @param capsuleId The unique string ID of the capsule.
     * @param title The title of the memory capsule.
     * @param summaryHash The sha256 or keccak256 hash of the capsule summary text.
     */
    function registerCapsule(
        string calldata capsuleId,
        string calldata title,
        bytes32 summaryHash
    ) external returns (bytes32) {
        bytes32 key = keccak256(abi.encodePacked(capsuleId));
        require(_registry[key].timestamp == 0, "Capsule already registered");

        _registry[key] = CapsuleRecord({
            capsuleId: capsuleId,
            title: title,
            summaryHash: summaryHash,
            timestamp: block.timestamp,
            owner: msg.sender
        });

        _allCapsuleHashes.push(key);

        emit CapsuleRegistered(
            key,
            capsuleId,
            title,
            summaryHash,
            msg.sender,
            block.timestamp
        );

        return key;
    }

    /**
     * @dev Get a registered capsule's details.
     */
    function getCapsule(string calldata capsuleId) external view returns (
        string memory id,
        string memory title,
        bytes32 summaryHash,
        uint256 timestamp,
        address owner
    ) {
        bytes32 key = keccak256(abi.encodePacked(capsuleId));
        CapsuleRecord memory record = _registry[key];
        require(record.timestamp > 0, "Capsule not found");
        return (
            record.capsuleId,
            record.title,
            record.summaryHash,
            record.timestamp,
            record.owner
        );
    }

    /**
     * @dev Check if a capsule is registered.
     */
    function isRegistered(string calldata capsuleId) external view returns (bool) {
        bytes32 key = keccak256(abi.encodePacked(capsuleId));
        return _registry[key].timestamp > 0;
    }

    /**
     * @dev Get total number of registered capsules.
     */
    function totalCapsules() external view returns (uint256) {
        return _allCapsuleHashes.length;
    }
}
