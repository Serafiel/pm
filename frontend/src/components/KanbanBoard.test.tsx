import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

vi.mock("next/navigation", () => {
  const router = { push: vi.fn() };
  return { useRouter: () => router };
});

beforeEach(() => {
  global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
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
    return Promise.resolve({ ok: true, status: 200 } as Response);
  });
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
