import { describe, it, expect, beforeEach, vi } from "vitest"
import { forgotPassword, resetPassword } from "@/api/auth"

// Mock the apiClient so we don't make real HTTP calls
vi.mock("@/api/client", () => ({
  apiClient: {
    post: vi.fn(),
  },
}))

import { apiClient } from "@/api/client"

const mockedPost = vi.mocked(apiClient.post)

describe("forgotPassword", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("calls POST /auth/forgot-password with email", async () => {
    const mockResponse = { message: "If that email is registered, a reset link has been sent." }
    mockedPost.mockResolvedValueOnce(mockResponse)

    const result = await forgotPassword({ email: "test@example.com" })

    expect(mockedPost).toHaveBeenCalledWith("/auth/forgot-password", {
      email: "test@example.com",
    })
    expect(result).toEqual(mockResponse)
  })
})

describe("resetPassword", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("calls POST /auth/reset-password with token and new password", async () => {
    const mockResponse = { message: "Password has been reset successfully" }
    mockedPost.mockResolvedValueOnce(mockResponse)

    const result = await resetPassword({
      token: "abc123token",
      new_password: "newpassword123",
    })

    expect(mockedPost).toHaveBeenCalledWith("/auth/reset-password", {
      token: "abc123token",
      new_password: "newpassword123",
    })
    expect(result).toEqual(mockResponse)
  })
})
