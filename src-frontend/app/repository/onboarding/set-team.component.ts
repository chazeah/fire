import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { Repository } from '../repository.model';

@Component({
    templateUrl: './set-team.component.html'
})
export class SetTeamComponent implements OnInit {
    repository: Repository;

    constructor(
        private route: ActivatedRoute,
        private router: Router
    ) {}

    ngOnInit() {
        let data = this.route.parent.snapshot.data as { repository: Repository };
        this.repository = data.repository;
    }
}
