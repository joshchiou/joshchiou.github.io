# Counts the publications in the scholar bibliography at build time and exposes them as
# site.data.publication_stats, so the homepage and /publications/ always show the same numbers
# as the list itself. Entries with `counted = {false}` (the PhD thesis) are listed but not counted.
# Top journals come from `top_journals` in _config.yml, kept in that order.
require "bibtex"

module PublicationStats
  class Generator < Jekyll::Generator
    safe true
    priority :highest

    def generate(site)
      scholar = site.config["scholar"] || {}
      path = File.join(site.source, scholar["source"] || "_bibliography",
                       "#{File.basename(scholar["bibliography"] || "papers", ".bib")}.bib")
      entries = BibTeX.parse(File.read(path, encoding: "utf-8")).data.select { |item| item.is_a?(BibTeX::Entry) }
      entries = entries.reject { |entry| entry[:counted].to_s == "false" }

      top_journals = (site.config["top_journals"] || []).map do |name|
        { "name" => name, "count" => entries.count { |entry| entry[:journal].to_s.strip == name } }
      end
      top_journals = top_journals.select { |j| j["count"].positive? }

      site.data["publication_stats"] = {
        "total" => entries.size,
        "selected" => entries.count { |entry| entry[:selected].to_s == "true" },
        "top_journal_papers" => top_journals.sum { |j| j["count"] },
        "top_journals" => top_journals,
      }
    end
  end
end
