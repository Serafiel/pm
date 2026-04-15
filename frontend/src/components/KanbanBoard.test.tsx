import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

vi.mock("next/navigation", () => {
  const router = { push: vi.fn() };
  return { useRouter: () => router };
});

function makeFetch(aiResponse?: { reply: string; board_updated: boolean }) {
  return vi.fn().mockImplementation((url: string, options?: RequestInit) => {
    if (url === "/api/board") {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(initialData),
      } as Response);
    }
    if (options?.method === "POST" && url === "/api/board/cards") {
      const body = JSON.parse(options.body as string);
      return Promise.resolve({
        ok: true,
        status: 201,
        json: () => Promise.resolve({ id: "new-card-id", title: body.title, details: body.details ?? "" }),
      } as Response);
    }
    if (options?.method === "POST" && url === "/api/ai/chat") {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(aiResponse ?? { reply: "Got it!", board_updated: false }),
      } as Response);
    }
    return Promise.resolve({ ok: true, status: 200 } as Response);
  });
}

beforeEach(() => {
  global.fetch = makeFetch();
});

describe("KanbanBoard", () => {
  it("renders five columns", async () => {
    render(<KanbanBoard />);
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const columns = await screen.findAllByTestId(/column-/i);
    const input = within(columns[0]).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("sidebar is hidden initially", async () => {
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);
    expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  });

  it("opens and closes the AI chat sidebar", async () => {
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);
    await userEvent.click(screen.getByRole("button", { name: /ai chat/i }));
    expect(screen.getByRole("complementary")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /close ai chat/i }));
    expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  });

  it("sends a message and shows the AI reply", async () => {
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);
    await userEvent.click(screen.getByRole("button", { name: /ai chat/i }));

    const input = screen.getByPlaceholderText(/ask or instruct/i);
    await userEvent.type(input, "How many cards are there?");
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(await screen.findByText("How many cards are there?")).toBeInTheDocument();
    expect(await screen.findByText("Got it!")).toBeInTheDocument();
  });

  it("re-fetches the board when board_updated is true", async () => {
    global.fetch = makeFetch({ reply: "Done!", board_updated: true });
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);
    await userEvent.click(screen.getByRole("button", { name: /ai chat/i }));

    await userEvent.type(screen.getByPlaceholderText(/ask or instruct/i), "Move a card");
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    await screen.findByText("Done!");
    // /api/board called once on mount, once after board_updated
    const boardCalls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls.filter(
      ([url]: [string]) => url === "/api/board"
    );
    expect(boardCalls.length).toBe(2);
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    const columns = await screen.findAllByTestId(/column-/i);
    const column = columns[0];

    await userEvent.click(within(column).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(column).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(await within(column).findByText("New card")).toBeInTheDocument();

    await userEvent.click(within(column).getByRole("button", { name: /delete new card/i }));
    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });
});
