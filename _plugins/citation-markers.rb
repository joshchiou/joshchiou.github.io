# Co-first authors are marked with `*` in papers.bib so the publication list can show them, but
# jekyll-scholar copies the marker into inline citations ("(Wang* et al., 2023)"). Strip marker
# symbols from inline citation links after rendering.
module CitationMarkers
  CITATION = %r{(<a class="citation"[^>]*>)([^<]*)(</a>)}.freeze

  def self.strip(html)
    return html unless html&.include?('class="citation"')

    html.gsub(CITATION) { "#{Regexp.last_match(1)}#{Regexp.last_match(2).delete('*∗†‡')}#{Regexp.last_match(3)}" }
  end
end

Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  doc.output = CitationMarkers.strip(doc.output)
end
